"""
Erlang C Queuing Theory for Specialist Coverage Optimization.

Implements telecommunications queuing theory (Erlang C formula) for
optimal specialist staffing. Used to determine minimum staff needed
to meet service level targets while avoiding over-staffing.

Key Concepts:
- Erlang B: Probability all servers busy (blocking, no queue)
- Erlang C: Probability of waiting (with queue)
- Service Level: % of calls answered within target time
- Occupancy: Average utilization of servers

Typical Medical Applications:
- ER specialist coverage (e.g., need orthopedic surgeon within 15 min)
- Call schedule optimization (minimizing wait for consultant callback)
- Procedure coverage (ensuring specialist available for emergent cases)

Formulas:
- Offered Load: A = λ * μ (arrival_rate * avg_service_time)
- Erlang B: P(blocking) = (A^c / c!) / Σ(k=0 to c)(A^k / k!)
- Erlang C: P(wait) = Erlang_B / (1 - (A/c)(1 - Erlang_B))
- Avg Wait Time: W = P(wait) * μ / (c - A)
- Service Level: P(wait within target) = 1 - P(wait) * e^(-(c-A)t/μ)
"""

import functools
import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SpecialistCoverage:
    """Recommended specialist coverage configuration."""

    specialty: str
    required_specialists: int
    predicted_wait_probability: float  # P(wait > 0)
    offered_load: float  # A = λ * μ
    service_level: float  # P(answer within target time)


@dataclass
class ErlangMetrics:
    """Complete Erlang C metrics for a configuration."""

    wait_probability: float  # P(wait > 0)
    avg_wait_time: float  # Average wait time in same units as service_time
    service_level: float  # P(answer within target time)
    occupancy: float  # Average server utilization (0.0 to 1.0)


class ErlangCCalculator:
    """
    Calculator for Erlang C queuing theory metrics.

    Implements classic telecommunications formulas for M/M/c queues:
    - Poisson arrivals (M)
    - Exponential service times (M)
    - c servers with infinite queue

    This models specialist coverage where:
    - Arrivals = Emergency cases requiring specialist
    - Service time = Time specialist engaged per case
    - Servers = Number of specialists on duty
    """

    def __init__(self) -> None:
        """Initialize Erlang C calculator."""
        self._erlang_b_cache = {}
        self._erlang_c_cache = {}

    def erlang_b(self, offered_load: float, servers: int) -> float:
        """
        Calculate Erlang B (blocking probability).

        Erlang B gives probability all servers are busy (no queue).
        Used as intermediate step for Erlang C.

        Formula: B(A, c) = (A^c / c!) / Σ(k=0 to c)(A^k / k!)

        Args:
            offered_load: A = λ * μ (arrival_rate * avg_service_time)
            servers: Number of servers (specialists)

        Returns:
            Probability all servers busy (0.0 to 1.0)

        Example:
            >>> calc = ErlangCCalculator()
            >>> calc.erlang_b(offered_load=5.0, servers=8)
            0.0349  # 3.49% chance all 8 specialists busy
        """
        if servers <= 0:
            return 1.0
        if offered_load <= 0:
            return 0.0

            # Check cache
        cache_key = (offered_load, servers)
        if cache_key in self._erlang_b_cache:
            return self._erlang_b_cache[cache_key]

            # Calculate using recursive formula for numerical stability
            # B(A, c) = (A * B(A, c-1)) / (c + A * B(A, c-1))
        b = 1.0
        for i in range(1, servers + 1):
            b = (offered_load * b) / (i + offered_load * b)

        self._erlang_b_cache[cache_key] = b
        return b

    def erlang_c(self, offered_load: float, servers: int) -> float:
        """
        Calculate Erlang C (probability of waiting).

        Erlang C gives probability a caller must wait in queue.
        Used for systems with infinite queue (like medical specialist coverage).

        Formula: C(A, c) = B(A, c) / (1 - (A/c)(1 - B(A, c)))

        Args:
            offered_load: A = λ * μ (arrival_rate * avg_service_time)
            servers: Number of servers (specialists)

        Returns:
            Probability of waiting (0.0 to 1.0)

        Raises:
            ValueError: If offered_load >= servers (unstable queue)

        Example:
            >>> calc = ErlangCCalculator()
            >>> calc.erlang_c(offered_load=5.0, servers=8)
            0.0745  # 7.45% of cases will wait for specialist
        """
        if servers <= 0:
            return 1.0
        if offered_load <= 0:
            return 0.0

            # Check stability: offered_load must be < servers
        if offered_load >= servers:
            raise ValueError(
                f"Unstable queue: offered_load ({offered_load:.2f}) >= "
                f"servers ({servers}). Queue will grow indefinitely."
            )

            # Check cache
        cache_key = (offered_load, servers)
        if cache_key in self._erlang_c_cache:
            return self._erlang_c_cache[cache_key]

            # Calculate Erlang C
        b = self.erlang_b(offered_load, servers)
        rho = offered_load / servers  # Utilization per server

        c = b / (1 - rho * (1 - b))

        self._erlang_c_cache[cache_key] = c
        return c

    def calculate_wait_probability(
        self,
        arrival_rate: float,
        service_time: float,
        servers: int,
    ) -> float:
        """
        Calculate probability a request must wait.

        Convenience wrapper around erlang_c() that takes arrival rate
        and service time separately.

        Args:
            arrival_rate: λ, average requests per time unit (e.g., 2.5 cases/hour)
            service_time: μ, average time to handle request (e.g., 0.5 hours)
            servers: Number of servers (specialists)

        Returns:
            Probability of waiting (0.0 to 1.0)

        Example:
            >>> calc = ErlangCCalculator()
            >>> calc.calculate_wait_probability(
            ...     arrival_rate=2.5,  # 2.5 cases/hour
            ...     service_time=0.5,  # 30 min per case
            ...     servers=3
            ... )
            0.127  # 12.7% chance of waiting
        """
        offered_load = arrival_rate * service_time
        return self.erlang_c(offered_load, servers)

    def calculate_avg_wait_time(
        self,
        arrival_rate: float,
        service_time: float,
        servers: int,
    ) -> float:
        """
        Calculate average wait time for requests that must wait.

        Formula: W = P(wait) * μ / (c - A)

        Where:
        - P(wait) = Erlang C probability
        - μ = service_time
        - c = servers
        - A = offered_load

        Args:
            arrival_rate: λ, average requests per time unit
            service_time: μ, average time to handle request
            servers: Number of servers (specialists)

        Returns:
            Average wait time in same units as service_time

        Example:
            >>> calc = ErlangCCalculator()
            >>> calc.calculate_avg_wait_time(
            ...     arrival_rate=2.5,  # 2.5 cases/hour
            ...     service_time=0.5,  # 30 min per case
            ...     servers=3
            ... )
            0.034  # ~2 minutes average wait (0.034 hours)
        """
        offered_load = arrival_rate * service_time

        if offered_load >= servers:
            raise ValueError(
                f"Unstable queue: offered_load ({offered_load:.2f}) >= "
                f"servers ({servers})"
            )

        prob_wait = self.erlang_c(offered_load, servers)

        # Average wait time: W = P(wait) * μ / (c - A)
        avg_wait = prob_wait * service_time / (servers - offered_load)

        return avg_wait

    def calculate_service_level(
        self,
        arrival_rate: float,
        service_time: float,
        servers: int,
        target_wait: float,
    ) -> float:
        """
        Calculate service level (% answered within target time).

        Service level is the probability a request is answered within
        the target wait time.

        Formula: SL = 1 - P(wait) * e^(-(c-A)*t/μ)

        Where:
        - P(wait) = Erlang C probability
        - c = servers
        - A = offered_load
        - t = target_wait
        - μ = service_time

        Args:
            arrival_rate: λ, average requests per time unit
            service_time: μ, average time to handle request
            servers: Number of servers (specialists)
            target_wait: Target wait time (in same units as service_time)

        Returns:
            Service level as probability (0.0 to 1.0)

        Example:
            >>> calc = ErlangCCalculator()
            >>> calc.calculate_service_level(
            ...     arrival_rate=2.5,  # 2.5 cases/hour
            ...     service_time=0.5,  # 30 min per case
            ...     servers=3,
            ...     target_wait=0.25  # 15 min target
            ... )
            0.957  # 95.7% answered within 15 min
        """
        offered_load = arrival_rate * service_time

        if offered_load >= servers:
            raise ValueError(
                f"Unstable queue: offered_load ({offered_load:.2f}) >= "
                f"servers ({servers})"
            )

        prob_wait = self.erlang_c(offered_load, servers)

        # Service level formula
        exponent = -(servers - offered_load) * target_wait / service_time
        service_level = 1 - prob_wait * np.exp(exponent)

        return max(0.0, min(1.0, service_level))

    def calculate_occupancy(
        self,
        arrival_rate: float,
        service_time: float,
        servers: int,
    ) -> float:
        """
        Calculate occupancy (average server utilization).

        Occupancy is the fraction of time servers are busy.
        Equivalent to offered_load / servers.

        Args:
            arrival_rate: λ, average requests per time unit
            service_time: μ, average time to handle request
            servers: Number of servers (specialists)

        Returns:
            Occupancy as fraction (0.0 to 1.0)

        Example:
            >>> calc = ErlangCCalculator()
            >>> calc.calculate_occupancy(
            ...     arrival_rate=2.5,  # 2.5 cases/hour
            ...     service_time=0.5,  # 30 min per case
            ...     servers=3
            ... )
            0.417  # 41.7% average utilization
        """
        if servers <= 0:
            return 1.0

        offered_load = arrival_rate * service_time
        occupancy = offered_load / servers

        return min(1.0, occupancy)

    def optimize_specialist_coverage(
        self,
        specialty: str,
        arrival_rate: float,
        service_time: float,
        target_wait_prob: float = 0.05,
        max_servers: int = 20,
    ) -> SpecialistCoverage:
        """
        Determine optimal specialist coverage for service level target.

        Finds minimum number of specialists needed to achieve target
        wait probability (e.g., 95% answered immediately = 5% wait prob).

        Algorithm:
        1. Start with minimum servers (ceil(offered_load) + 1)
        2. Calculate wait probability
        3. If above target, add server and retry
        4. Return first configuration meeting target

        Args:
            specialty: Name of specialty (e.g., "Orthopedic Surgery")
            arrival_rate: λ, average requests per time unit
            service_time: μ, average time to handle request
            target_wait_prob: Maximum acceptable wait probability (default 0.05 = 5%)
            max_servers: Maximum servers to consider (prevents infinite loop)

        Returns:
            SpecialistCoverage with optimal configuration

        Raises:
            ValueError: If target cannot be met within max_servers

        Example:
            >>> calc = ErlangCCalculator()
            >>> coverage = calc.optimize_specialist_coverage(
            ...     specialty="Orthopedic Surgery",
            ...     arrival_rate=2.5,  # 2.5 cases/hour
            ...     service_time=0.5,  # 30 min per case
            ...     target_wait_prob=0.05  # 5% max wait probability
            ... )
            >>> print(f"Need {coverage.required_specialists} specialists")
            Need 4 specialists
        """
        offered_load = arrival_rate * service_time

        # Minimum servers: must be > offered_load for stability
        min_servers = int(np.ceil(offered_load)) + 1

        logger.debug(
            f"Optimizing {specialty} coverage: "
            f"arrival_rate={arrival_rate:.2f}, "
            f"service_time={service_time:.2f}, "
            f"offered_load={offered_load:.2f}, "
            f"min_servers={min_servers}"
        )

        # Search for optimal server count
        for servers in range(min_servers, max_servers + 1):
            try:
                wait_prob = self.erlang_c(offered_load, servers)

                if wait_prob <= target_wait_prob:
                    # Found optimal configuration
                    # Calculate service level with typical target (15 min = 0.25 hours)
                    typical_target = service_time * 0.5  # Half of service time
                    service_level = self.calculate_service_level(
                        arrival_rate, service_time, servers, typical_target
                    )

                    logger.info(
                        f"Optimal {specialty} coverage: {servers} specialists "
                        f"(wait_prob={wait_prob:.3f}, service_level={service_level:.3f})"
                    )

                    return SpecialistCoverage(
                        specialty=specialty,
                        required_specialists=servers,
                        predicted_wait_probability=wait_prob,
                        offered_load=offered_load,
                        service_level=service_level,
                    )

            except ValueError:
                # Unstable configuration, try more servers
                continue

                # Target not achievable
        raise ValueError(
            f"Cannot meet target wait probability {target_wait_prob:.2%} "
            f"for {specialty} with up to {max_servers} specialists. "
            f"Offered load ({offered_load:.2f}) may be too high."
        )

    def calculate_metrics(
        self,
        arrival_rate: float,
        service_time: float,
        servers: int,
        target_wait: float | None = None,
    ) -> ErlangMetrics:
        """
        Calculate complete Erlang C metrics for a configuration.

        Convenience method that calculates all metrics at once.

        Args:
            arrival_rate: λ, average requests per time unit
            service_time: μ, average time to handle request
            servers: Number of servers (specialists)
            target_wait: Target wait time for service level (optional)

        Returns:
            ErlangMetrics with all calculated values

        Example:
            >>> calc = ErlangCCalculator()
            >>> metrics = calc.calculate_metrics(
            ...     arrival_rate=2.5,
            ...     service_time=0.5,
            ...     servers=3,
            ...     target_wait=0.25
            ... )
            >>> print(f"Wait prob: {metrics.wait_probability:.1%}")
            Wait prob: 12.7%
        """
        if target_wait is None:
            target_wait = service_time * 0.5  # Default to half service time

        wait_prob = self.calculate_wait_probability(arrival_rate, service_time, servers)
        avg_wait = self.calculate_avg_wait_time(arrival_rate, service_time, servers)
        service_level = self.calculate_service_level(
            arrival_rate, service_time, servers, target_wait
        )
        occupancy = self.calculate_occupancy(arrival_rate, service_time, servers)

        return ErlangMetrics(
            wait_probability=wait_prob,
            avg_wait_time=avg_wait,
            service_level=service_level,
            occupancy=occupancy,
        )

    def generate_staffing_table(
        self,
        arrival_rate: float,
        service_time: float,
        min_servers: int | None = None,
        max_servers: int | None = None,
    ) -> list[dict]:
        """
        Generate staffing table showing metrics for different server counts.

        Useful for decision-making: shows trade-off between staff count
        and service quality.

        Args:
            arrival_rate: λ, average requests per time unit
            service_time: μ, average time to handle request
            min_servers: Minimum servers to analyze (default: ceil(offered_load) + 1)
            max_servers: Maximum servers to analyze (default: min_servers + 10)

        Returns:
            List of dicts with staffing metrics for each server count

        Example:
            >>> calc = ErlangCCalculator()
            >>> table = calc.generate_staffing_table(
            ...     arrival_rate=2.5,
            ...     service_time=0.5
            ... )
            >>> for row in table:
            ...     print(f"{row['servers']} servers: "
            ...           f"{row['wait_probability']:.1%} wait prob")
        """
        offered_load = arrival_rate * service_time

        if min_servers is None:
            min_servers = int(np.ceil(offered_load)) + 1
        if max_servers is None:
            max_servers = min_servers + 10

        table = []
        target_wait = service_time * 0.5

        for servers in range(min_servers, max_servers + 1):
            try:
                metrics = self.calculate_metrics(
                    arrival_rate, service_time, servers, target_wait
                )

                table.append(
                    {
                        "servers": servers,
                        "offered_load": offered_load,
                        "wait_probability": metrics.wait_probability,
                        "avg_wait_time": metrics.avg_wait_time,
                        "service_level": metrics.service_level,
                        "occupancy": metrics.occupancy,
                    }
                )

            except ValueError:
                # Skip unstable configurations
                continue

        return table
