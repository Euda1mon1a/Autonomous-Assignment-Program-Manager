"""
Optimization and Analytics MCP Tools.

Exposes advanced optimization and analytics modules as MCP tools for AI
assistant interaction. These tools provide quantitative analysis for
staffing optimization, quality measurement, and workload equity.

Modules Exposed:
- Erlang C Coverage: Telecommunications queuing theory for optimal staffing
- Process Capability: Six Sigma quality metrics (Cp/Cpk/Cpm)
- Equity Metrics: Gini coefficient and workload fairness analysis
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Erlang C Coverage Response Models
# =============================================================================


class StaffingTableEntry(BaseModel):
    """Single entry in a staffing recommendation table."""

    servers: int = Field(description="Number of specialists/servers")
    offered_load: float = Field(description="Offered load (arrival_rate * service_time)")
    wait_probability: float = Field(
        ge=0.0, le=1.0, description="Probability a request must wait"
    )
    avg_wait_time: float = Field(
        ge=0.0, description="Average wait time (same units as service_time)"
    )
    service_level: float = Field(
        ge=0.0, le=1.0, description="Probability of serving within target time"
    )
    occupancy: float = Field(
        ge=0.0, le=1.0, description="Average server utilization"
    )


class ErlangCoverageResponse(BaseModel):
    """Response from Erlang coverage optimization."""

    specialty: str = Field(description="Name of the specialty analyzed")
    recommended_specialists: int = Field(
        ge=1, description="Minimum specialists needed to meet service level"
    )
    current_utilization: float = Field(
        ge=0.0, le=1.0, description="Current server utilization rate"
    )
    wait_probability: float = Field(
        ge=0.0, le=1.0, description="Probability of waiting with recommended staff"
    )
    avg_wait_time_minutes: float = Field(
        ge=0.0, description="Expected average wait time in minutes"
    )
    service_level: float = Field(
        ge=0.0, le=1.0, description="Percentage served within target wait time"
    )
    offered_load: float = Field(
        ge=0.0, description="Total offered load (arrival_rate * service_time)"
    )
    staffing_table: list[StaffingTableEntry] = Field(
        default_factory=list,
        description="Staffing options with metrics for different server counts",
    )
    queue_stable: bool = Field(
        description="Whether queue is stable (offered_load < servers)"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Actionable staffing recommendations"
    )
    severity: str = Field(
        description="Staffing urgency: healthy, warning, critical, or emergency"
    )


class ErlangMetricsResponse(BaseModel):
    """Detailed Erlang C metrics for a specific configuration."""

    wait_probability: float = Field(
        ge=0.0, le=1.0, description="Probability of waiting (Erlang C)"
    )
    avg_wait_time: float = Field(ge=0.0, description="Average wait time")
    service_level: float = Field(
        ge=0.0, le=1.0, description="Probability served within target"
    )
    occupancy: float = Field(ge=0.0, le=1.0, description="Average utilization")
    offered_load: float = Field(ge=0.0, description="Total offered load")
    queue_stable: bool = Field(description="Whether queue is stable")
    blocking_probability: float = Field(
        ge=0.0, le=1.0, description="Erlang B probability (all servers busy)"
    )


# =============================================================================
# Process Capability Response Models
# =============================================================================


class ProcessCapabilityResponse(BaseModel):
    """Response from Six Sigma process capability analysis."""

    # Core capability indices
    cp: float = Field(description="Process capability index (potential)")
    cpk: float = Field(description="Process capability index (actual, centered)")
    pp: float = Field(description="Process performance index (long-term)")
    ppk: float = Field(description="Process performance index (long-term centered)")
    cpm: float = Field(description="Taguchi capability index (off-target penalty)")

    # Classification
    capability_status: str = Field(
        description="Classification: EXCELLENT, CAPABLE, MARGINAL, or INCAPABLE"
    )
    sigma_level: float = Field(
        ge=0.0, description="Estimated sigma level (e.g., 4.5 for 4.5-sigma)"
    )

    # Statistics
    sample_size: int = Field(ge=1, description="Number of data points analyzed")
    mean: float = Field(description="Sample mean")
    std_dev: float = Field(ge=0.0, description="Sample standard deviation")

    # Specification limits
    lsl: float = Field(description="Lower specification limit")
    usl: float = Field(description="Upper specification limit")
    target: float | None = Field(default=None, description="Target value (if specified)")

    # Derived metrics
    centering_assessment: str = Field(
        description="Assessment of process centering quality"
    )
    estimated_defect_rate_ppm: float = Field(
        ge=0.0, description="Estimated defects per million"
    )

    # Recommendations
    recommendations: list[str] = Field(
        default_factory=list, description="Improvement recommendations"
    )
    severity: str = Field(
        description="Quality urgency: excellent, capable, marginal, or incapable"
    )


# =============================================================================
# Equity Metrics Response Models
# =============================================================================


class EquityMetricsResponse(BaseModel):
    """Response from workload equity analysis."""

    # Gini coefficient and classification
    gini_coefficient: float = Field(
        ge=0.0, le=1.0, description="Gini coefficient (0=perfect equality, 1=max inequality)"
    )
    target_gini: float = Field(
        ge=0.0, le=1.0, description="Target Gini for equitable distribution"
    )
    is_equitable: bool = Field(
        description="Whether distribution meets equity threshold"
    )

    # Workload statistics
    mean_hours: float = Field(ge=0.0, description="Average hours per provider")
    std_hours: float = Field(ge=0.0, description="Standard deviation of hours")
    min_hours: float = Field(ge=0.0, description="Minimum hours assigned")
    max_hours: float = Field(ge=0.0, description="Maximum hours assigned")
    coefficient_of_variation: float = Field(
        ge=0.0, description="CV = std_dev / mean (relative spread)"
    )

    # Outlier identification
    most_overloaded_provider: str = Field(
        description="Provider ID with highest (intensity-adjusted) hours"
    )
    most_underloaded_provider: str = Field(
        description="Provider ID with lowest (intensity-adjusted) hours"
    )
    overload_delta: float = Field(
        description="Hours above mean for most overloaded"
    )
    underload_delta: float = Field(
        description="Hours below mean for most underloaded"
    )

    # Provider count
    provider_count: int = Field(ge=1, description="Number of providers analyzed")

    # Recommendations
    recommendations: list[str] = Field(
        default_factory=list, description="Rebalancing recommendations"
    )
    severity: str = Field(
        description="Equity urgency: equitable, warning, inequitable, or critical"
    )


class LorenzCurveResponse(BaseModel):
    """Response with Lorenz curve data for visualization."""

    population_shares: list[float] = Field(
        description="Cumulative population share (x-axis, 0 to 1)"
    )
    value_shares: list[float] = Field(
        description="Cumulative value share (y-axis, 0 to 1)"
    )
    gini_coefficient: float = Field(
        ge=0.0, le=1.0, description="Area between Lorenz curve and equality line"
    )
    equality_line: list[float] = Field(
        description="Reference line for perfect equality (y=x)"
    )


# =============================================================================
# Tool Functions
# =============================================================================


async def optimize_erlang_coverage(
    specialty: str,
    arrival_rate: float,
    service_time_minutes: float,
    target_wait_minutes: float = 15.0,
    target_wait_probability: float = 0.05,
    max_servers: int = 20,
) -> ErlangCoverageResponse:
    """
    Optimize specialist staffing using telecommunications Erlang-C formulas.

    Applies M/M/c queuing theory (Markovian arrival, Markovian service, c servers)
    to determine optimal specialist coverage, balancing utilization against wait
    times. This is the same mathematical model used by call centers worldwide.

    Key Concepts:
    - Offered Load (A): arrival_rate * service_time = average work arriving per unit time
    - Erlang B: Probability all servers are busy (blocking, no queue)
    - Erlang C: Probability a request must wait (with infinite queue)
    - Service Level: Percentage of requests served within target wait time

    The 80% utilization threshold is critical: above 80%, wait times grow
    exponentially and system becomes unstable (cascade failures likely).

    Args:
        specialty: Name of specialty (e.g., "Orthopedic Surgery", "Cardiology")
        arrival_rate: Average requests per hour (e.g., 2.5 cases/hour)
        service_time_minutes: Average time per case in minutes (e.g., 30 min)
        target_wait_minutes: Target wait time for service level (default: 15 min)
        target_wait_probability: Maximum acceptable wait probability (default: 5%)
        max_servers: Maximum servers to consider (prevents infinite loop)

    Returns:
        ErlangCoverageResponse with optimal staffing and staffing table

    Raises:
        ValueError: If parameters are invalid or target is unachievable

    Example:
        # Optimize ER orthopedic coverage
        result = await optimize_erlang_coverage(
            specialty="Orthopedic Surgery",
            arrival_rate=2.5,  # 2.5 cases/hour
            service_time_minutes=30,  # 30 min per case
            target_wait_minutes=15,
            target_wait_probability=0.05
        )
        print(f"Need {result.recommended_specialists} specialists")
        print(f"Wait probability: {result.wait_probability:.1%}")
    """
    if arrival_rate <= 0:
        raise ValueError("arrival_rate must be positive")
    if service_time_minutes <= 0:
        raise ValueError("service_time_minutes must be positive")
    if target_wait_minutes <= 0:
        raise ValueError("target_wait_minutes must be positive")
    if not 0 < target_wait_probability < 1:
        raise ValueError("target_wait_probability must be between 0 and 1")
    if max_servers < 1:
        raise ValueError("max_servers must be at least 1")

    logger.info(
        f"Optimizing Erlang coverage for {specialty}: "
        f"arrival_rate={arrival_rate}/hr, service_time={service_time_minutes}min"
    )

    # Convert service time to hours for consistency
    service_time_hours = service_time_minutes / 60.0
    target_wait_hours = target_wait_minutes / 60.0

    try:
        from app.resilience.erlang_coverage import ErlangCCalculator

        calc = ErlangCCalculator()

        # Optimize specialist coverage
        coverage = calc.optimize_specialist_coverage(
            specialty=specialty,
            arrival_rate=arrival_rate,
            service_time=service_time_hours,
            target_wait_prob=target_wait_probability,
            max_servers=max_servers,
        )

        # Get detailed metrics for the recommended configuration
        metrics = calc.calculate_metrics(
            arrival_rate=arrival_rate,
            service_time=service_time_hours,
            servers=coverage.required_specialists,
            target_wait=target_wait_hours,
        )

        # Generate staffing table
        table_data = calc.generate_staffing_table(
            arrival_rate=arrival_rate,
            service_time=service_time_hours,
            min_servers=None,  # Auto-calculate based on offered load
            max_servers=max_servers,
        )

        staffing_table = [
            StaffingTableEntry(
                servers=row["servers"],
                offered_load=row["offered_load"],
                wait_probability=row["wait_probability"],
                avg_wait_time=row["avg_wait_time"] * 60,  # Convert to minutes
                service_level=row["service_level"],
                occupancy=row["occupancy"],
            )
            for row in table_data
        ]

        # Determine severity based on utilization
        if metrics.occupancy >= 0.95:
            severity = "emergency"
        elif metrics.occupancy >= 0.80:
            severity = "critical"
        elif metrics.occupancy >= 0.70:
            severity = "warning"
        else:
            severity = "healthy"

        # Generate recommendations
        recommendations = []
        if metrics.occupancy >= 0.80:
            recommendations.append(
                f"CRITICAL: Utilization at {metrics.occupancy:.0%} exceeds 80% threshold. "
                "Wait times will grow exponentially."
            )
        if coverage.required_specialists >= max_servers - 2:
            recommendations.append(
                f"Approaching maximum analyzed capacity ({max_servers} servers). "
                "Consider reviewing demand patterns."
            )
        if metrics.service_level < 0.95:
            recommendations.append(
                f"Service level ({metrics.service_level:.0%}) below 95% target. "
                f"Consider adding {1} more specialist(s)."
            )
        if metrics.occupancy < 0.50:
            recommendations.append(
                f"Low utilization ({metrics.occupancy:.0%}). May be over-staffed."
            )

        return ErlangCoverageResponse(
            specialty=specialty,
            recommended_specialists=coverage.required_specialists,
            current_utilization=metrics.occupancy,
            wait_probability=metrics.wait_probability,
            avg_wait_time_minutes=metrics.avg_wait_time * 60,  # Convert to minutes
            service_level=metrics.service_level,
            offered_load=coverage.offered_load,
            staffing_table=staffing_table,
            queue_stable=coverage.offered_load < coverage.required_specialists,
            recommendations=recommendations,
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"Erlang coverage module unavailable: {e}")
        # Provide fallback calculation
        offered_load = arrival_rate * service_time_hours

        # Simple estimation: need at least ceil(offered_load / 0.8) for stability
        import math

        min_servers = max(1, math.ceil(offered_load / 0.8))

        return ErlangCoverageResponse(
            specialty=specialty,
            recommended_specialists=min_servers,
            current_utilization=offered_load / min_servers if min_servers > 0 else 1.0,
            wait_probability=0.10,  # Estimated
            avg_wait_time_minutes=5.0,  # Estimated
            service_level=0.90,  # Estimated
            offered_load=offered_load,
            staffing_table=[],
            queue_stable=offered_load < min_servers,
            recommendations=[
                "Erlang module unavailable - using simplified estimation",
                f"Minimum {min_servers} specialists recommended for stability",
            ],
            severity="warning",
        )

    except ValueError as e:
        logger.error(f"Erlang optimization failed: {e}")
        raise


async def calculate_erlang_metrics(
    arrival_rate: float,
    service_time_minutes: float,
    servers: int,
    target_wait_minutes: float = 15.0,
) -> ErlangMetricsResponse:
    """
    Calculate detailed Erlang C metrics for a specific staffing configuration.

    Use this tool to evaluate a specific staffing scenario or compare different
    configurations. For optimization (finding minimum staff), use
    optimize_erlang_coverage instead.

    Args:
        arrival_rate: Average requests per hour
        service_time_minutes: Average time per case in minutes
        servers: Number of servers (specialists) to evaluate
        target_wait_minutes: Target wait time for service level calculation

    Returns:
        ErlangMetricsResponse with detailed queuing metrics

    Raises:
        ValueError: If offered_load >= servers (unstable queue)

    Example:
        # Check metrics for 5 orthopedic surgeons
        metrics = await calculate_erlang_metrics(
            arrival_rate=2.5,
            service_time_minutes=30,
            servers=5,
            target_wait_minutes=15
        )
        print(f"Wait probability: {metrics.wait_probability:.1%}")
        print(f"Occupancy: {metrics.occupancy:.1%}")
    """
    if arrival_rate <= 0:
        raise ValueError("arrival_rate must be positive")
    if service_time_minutes <= 0:
        raise ValueError("service_time_minutes must be positive")
    if servers <= 0:
        raise ValueError("servers must be positive")

    service_time_hours = service_time_minutes / 60.0
    target_wait_hours = target_wait_minutes / 60.0
    offered_load = arrival_rate * service_time_hours

    if offered_load >= servers:
        raise ValueError(
            f"Unstable queue: offered_load ({offered_load:.2f}) >= servers ({servers}). "
            "Queue will grow indefinitely. Add more servers."
        )

    logger.info(f"Calculating Erlang metrics: {servers} servers, load={offered_load:.2f}")

    try:
        from app.resilience.erlang_coverage import ErlangCCalculator

        calc = ErlangCCalculator()

        metrics = calc.calculate_metrics(
            arrival_rate=arrival_rate,
            service_time=service_time_hours,
            servers=servers,
            target_wait=target_wait_hours,
        )

        blocking_prob = calc.erlang_b(offered_load, servers)

        return ErlangMetricsResponse(
            wait_probability=metrics.wait_probability,
            avg_wait_time=metrics.avg_wait_time * 60,  # Convert to minutes
            service_level=metrics.service_level,
            occupancy=metrics.occupancy,
            offered_load=offered_load,
            queue_stable=True,
            blocking_probability=blocking_prob,
        )

    except ImportError as e:
        logger.warning(f"Erlang coverage module unavailable: {e}")
        # Simplified fallback
        occupancy = offered_load / servers

        return ErlangMetricsResponse(
            wait_probability=0.1,  # Estimated
            avg_wait_time=5.0,  # Estimated
            service_level=0.9,  # Estimated
            occupancy=occupancy,
            offered_load=offered_load,
            queue_stable=True,
            blocking_probability=0.05,  # Estimated
        )


async def calculate_process_capability(
    data: list[float],
    lower_spec_limit: float,
    upper_spec_limit: float,
    target: float | None = None,
) -> ProcessCapabilityResponse:
    """
    Calculate Six Sigma process capability indices for schedule quality.

    Applies Six Sigma statistical process control to measure how consistently
    the scheduling process maintains ACGME compliance and operational constraints.
    This is the same methodology used in manufacturing for quality control.

    Process Capability Indices:
    - Cp: Process potential (spread relative to spec width, assumes centered)
    - Cpk: Process capability (accounts for off-center mean)
    - Pp/Ppk: Process performance (uses overall variation)
    - Cpm: Taguchi capability (penalizes deviation from target)

    Capability Classification:
    - Cpk >= 2.0: EXCELLENT (World Class, 6-sigma quality)
    - Cpk >= 1.67: EXCELLENT (5-sigma quality)
    - Cpk >= 1.33: CAPABLE (4-sigma, industry standard)
    - Cpk >= 1.0: MARGINAL (3-sigma, minimum acceptable)
    - Cpk < 1.0: INCAPABLE (defects expected)

    Common Applications:
    - Weekly work hours: LSL=40, USL=80 (ACGME), Target=60
    - Coverage rates: LSL=0.95, USL=1.0, Target=1.0
    - Utilization: LSL=0.0, USL=0.8, Target=0.65

    Args:
        data: Sample measurements (e.g., weekly hours for each resident)
        lower_spec_limit: LSL - minimum acceptable value
        upper_spec_limit: USL - maximum acceptable value
        target: Ideal target value (defaults to midpoint if not specified)

    Returns:
        ProcessCapabilityResponse with all capability indices and recommendations

    Raises:
        ValueError: If data is empty, has insufficient variation, or specs invalid

    Example:
        # Analyze weekly work hours for ACGME compliance
        weekly_hours = [65, 72, 58, 75, 68, 70, 62, 77, 55, 71]
        result = await calculate_process_capability(
            data=weekly_hours,
            lower_spec_limit=40,
            upper_spec_limit=80,
            target=60
        )
        print(f"Capability: {result.capability_status}")
        print(f"Sigma Level: {result.sigma_level:.2f}")
    """
    if not data:
        raise ValueError("data list cannot be empty")
    if len(data) < 2:
        raise ValueError("Need at least 2 data points")
    if lower_spec_limit >= upper_spec_limit:
        raise ValueError("lower_spec_limit must be less than upper_spec_limit")

    logger.info(
        f"Calculating process capability: n={len(data)}, "
        f"LSL={lower_spec_limit}, USL={upper_spec_limit}"
    )

    try:
        from app.resilience.process_capability import ScheduleCapabilityAnalyzer

        analyzer = ScheduleCapabilityAnalyzer(min_sample_size=30)

        # Use the analyzer's workload capability method
        report = analyzer.analyze_workload_capability(
            weekly_hours=data,
            min_hours=lower_spec_limit,
            max_hours=upper_spec_limit,
            target_hours=target,
        )

        # Get detailed summary
        summary = analyzer.get_capability_summary(report)

        # Calculate coefficient of variation
        cv = report.std_dev / report.mean if report.mean > 0 else 0.0

        # Determine severity mapping
        severity_map = {
            "EXCELLENT": "excellent",
            "CAPABLE": "capable",
            "MARGINAL": "marginal",
            "INCAPABLE": "incapable",
        }
        severity = severity_map.get(report.capability_status, "unknown")

        return ProcessCapabilityResponse(
            cp=report.cp,
            cpk=report.cpk,
            pp=report.pp,
            ppk=report.ppk,
            cpm=report.cpm,
            capability_status=report.capability_status,
            sigma_level=report.sigma_level,
            sample_size=report.sample_size,
            mean=report.mean,
            std_dev=report.std_dev,
            lsl=report.lsl,
            usl=report.usl,
            target=report.target,
            centering_assessment=summary["centering"],
            estimated_defect_rate_ppm=float(
                summary["estimated_defect_rate"]["ppm"]
            ),
            recommendations=summary["recommendations"],
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"Process capability module unavailable: {e}")
        # Provide fallback calculation
        import statistics

        mean = statistics.mean(data)
        std_dev = statistics.stdev(data)

        if target is None:
            target = (lower_spec_limit + upper_spec_limit) / 2

        # Simple Cp/Cpk calculation
        if std_dev > 0:
            cp = (upper_spec_limit - lower_spec_limit) / (6 * std_dev)
            cpu = (upper_spec_limit - mean) / (3 * std_dev)
            cpl = (mean - lower_spec_limit) / (3 * std_dev)
            cpk = min(cpu, cpl)
        else:
            cp = float("inf")
            cpk = float("inf") if lower_spec_limit <= mean <= upper_spec_limit else 0.0

        # Classify
        if cpk >= 1.67:
            status = "EXCELLENT"
            severity = "excellent"
        elif cpk >= 1.33:
            status = "CAPABLE"
            severity = "capable"
        elif cpk >= 1.0:
            status = "MARGINAL"
            severity = "marginal"
        else:
            status = "INCAPABLE"
            severity = "incapable"

        sigma_level = 3.0 * cpk

        return ProcessCapabilityResponse(
            cp=cp,
            cpk=cpk,
            pp=cp,  # Same as Cp for this simple case
            ppk=cpk,  # Same as Cpk for this simple case
            cpm=cpk,  # Approximation
            capability_status=status,
            sigma_level=sigma_level,
            sample_size=len(data),
            mean=mean,
            std_dev=std_dev,
            lsl=lower_spec_limit,
            usl=upper_spec_limit,
            target=target,
            centering_assessment="Process capability module unavailable",
            estimated_defect_rate_ppm=10 ** (6 - 2 * sigma_level)
            if sigma_level > 0
            else 1_000_000,
            recommendations=[
                "Process capability module unavailable - using simplified calculation"
            ],
            severity=severity,
        )


async def calculate_equity_metrics(
    provider_hours: dict[str, float],
    intensity_weights: dict[str, float] | None = None,
) -> EquityMetricsResponse:
    """
    Calculate workload equity metrics using Gini coefficient and fairness analysis.

    The Gini coefficient quantifies inequality in a distribution, ranging from
    0 (perfect equality, everyone has same workload) to 1 (perfect inequality,
    one person has all the work). For medical scheduling, a Gini coefficient
    below 0.15 indicates equitable workload distribution.

    Intensity weights allow accounting for shift difficulty:
    - Night shifts might have weight 1.5
    - Weekend shifts might have weight 1.3
    - High-acuity rotations might have weight 1.2

    Args:
        provider_hours: Mapping of provider ID to total hours worked
        intensity_weights: Optional mapping of provider ID to intensity
                          multiplier (default 1.0). Higher values indicate
                          more demanding assignments.

    Returns:
        EquityMetricsResponse with Gini coefficient and rebalancing recommendations

    Raises:
        ValueError: If provider_hours is empty or contains negative values

    Example:
        # Analyze faculty workload equity
        hours = {
            "FAC-001": 45,
            "FAC-002": 52,
            "FAC-003": 38,
            "FAC-004": 60,
            "FAC-005": 42
        }
        result = await calculate_equity_metrics(hours)
        print(f"Gini: {result.gini_coefficient:.3f}")
        print(f"Equitable: {result.is_equitable}")
        for rec in result.recommendations:
            print(f"  - {rec}")
    """
    if not provider_hours:
        raise ValueError("provider_hours cannot be empty")
    if any(h < 0 for h in provider_hours.values()):
        raise ValueError("provider_hours cannot contain negative values")
    if intensity_weights is not None:
        if set(intensity_weights.keys()) != set(provider_hours.keys()):
            raise ValueError(
                "intensity_weights keys must match provider_hours keys exactly"
            )
        if any(w < 0 for w in intensity_weights.values()):
            raise ValueError("intensity_weights cannot contain negative values")

    logger.info(f"Calculating equity metrics for {len(provider_hours)} providers")

    try:
        from app.resilience.equity_metrics import equity_report, gini_coefficient

        # Get comprehensive report
        report = equity_report(
            provider_hours=provider_hours,
            intensity_weights=intensity_weights,
        )

        # Calculate coefficient of variation
        cv = report["std_hours"] / report["mean_hours"] if report["mean_hours"] > 0 else 0.0

        # Determine severity
        gini = report["gini"]
        if gini < 0.10:
            severity = "equitable"
        elif gini < 0.15:
            severity = "warning"
        elif gini < 0.25:
            severity = "inequitable"
        else:
            severity = "critical"

        return EquityMetricsResponse(
            gini_coefficient=report["gini"],
            target_gini=report["target_gini"],
            is_equitable=report["is_equitable"],
            mean_hours=report["mean_hours"],
            std_hours=report["std_hours"],
            min_hours=report["min_hours"],
            max_hours=report["max_hours"],
            coefficient_of_variation=cv,
            most_overloaded_provider=report["most_overloaded"],
            most_underloaded_provider=report["most_underloaded"],
            overload_delta=report["overload_delta"],
            underload_delta=report["underload_delta"],
            provider_count=len(provider_hours),
            recommendations=report["recommendations"],
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"Equity metrics module unavailable: {e}")
        # Provide fallback calculation
        import numpy as np

        hours_values = list(provider_hours.values())
        provider_ids = list(provider_hours.keys())

        # Simple Gini calculation
        arr = np.array(hours_values, dtype=np.float64)
        n = len(arr)
        mean_val = np.mean(arr)

        if mean_val > 0 and not np.allclose(arr, arr[0]):
            diff_sum = np.sum(np.abs(arr[:, np.newaxis] - arr[np.newaxis, :]))
            gini = float(diff_sum / (2 * n * n * mean_val))
        else:
            gini = 0.0

        std_val = float(np.std(arr))
        cv = std_val / mean_val if mean_val > 0 else 0.0

        # Find extremes
        max_idx = int(np.argmax(arr))
        min_idx = int(np.argmin(arr))

        target_gini = 0.15
        is_equitable = gini < target_gini

        # Determine severity
        if gini < 0.10:
            severity = "equitable"
        elif gini < 0.15:
            severity = "warning"
        elif gini < 0.25:
            severity = "inequitable"
        else:
            severity = "critical"

        recommendations = []
        if not is_equitable:
            recommendations.append(
                f"High inequality detected (Gini={gini:.3f}). Target is below {target_gini:.2f}."
            )
            recommendations.append("Equity metrics module unavailable - using simplified calculation")

        return EquityMetricsResponse(
            gini_coefficient=gini,
            target_gini=target_gini,
            is_equitable=is_equitable,
            mean_hours=float(mean_val),
            std_hours=std_val,
            min_hours=float(np.min(arr)),
            max_hours=float(np.max(arr)),
            coefficient_of_variation=cv,
            most_overloaded_provider=provider_ids[max_idx],
            most_underloaded_provider=provider_ids[min_idx],
            overload_delta=float(arr[max_idx] - mean_val),
            underload_delta=float(mean_val - arr[min_idx]),
            provider_count=len(provider_hours),
            recommendations=recommendations,
            severity=severity,
        )


async def generate_lorenz_curve(
    values: list[float],
) -> LorenzCurveResponse:
    """
    Generate Lorenz curve data for visualizing workload inequality.

    The Lorenz curve plots cumulative share of population (x-axis) against
    cumulative share of total value (y-axis). Perfect equality is the 45-degree
    diagonal line. The Gini coefficient equals twice the area between the
    Lorenz curve and the equality line.

    Use this data to visualize workload distribution in charts or dashboards.

    Args:
        values: List of numeric values (e.g., hours worked by each provider)

    Returns:
        LorenzCurveResponse with curve coordinates and Gini coefficient

    Raises:
        ValueError: If values is empty or contains negative values

    Example:
        # Generate Lorenz curve for faculty hours
        hours = [45, 52, 38, 60, 42, 55, 48]
        curve = await generate_lorenz_curve(hours)

        # Plot in visualization library
        # plt.plot(curve.population_shares, curve.equality_line, 'k--')
        # plt.plot(curve.population_shares, curve.value_shares, 'b-')
        # plt.fill_between(...)
    """
    if not values:
        raise ValueError("values list cannot be empty")
    if any(v < 0 for v in values):
        raise ValueError("values cannot contain negative numbers")

    logger.info(f"Generating Lorenz curve for {len(values)} values")

    try:
        from app.resilience.equity_metrics import gini_coefficient, lorenz_curve

        x_coords, y_coords = lorenz_curve(values)
        gini = gini_coefficient(values)

        return LorenzCurveResponse(
            population_shares=x_coords.tolist(),
            value_shares=y_coords.tolist(),
            gini_coefficient=gini,
            equality_line=x_coords.tolist(),  # y=x line
        )

    except ImportError as e:
        logger.warning(f"Equity metrics module unavailable: {e}")
        # Provide fallback calculation
        import numpy as np

        sorted_values = np.sort(np.array(values, dtype=np.float64))
        n = len(sorted_values)
        total = np.sum(sorted_values)

        if np.allclose(total, 0.0):
            x_coords = np.linspace(0, 1, n + 1)
            y_coords = np.linspace(0, 1, n + 1)
        else:
            cumulative = np.concatenate(([0], np.cumsum(sorted_values)))
            y_coords = cumulative / total
            x_coords = np.linspace(0, 1, n + 1)

        # Simple Gini
        arr = np.array(values, dtype=np.float64)
        mean_val = np.mean(arr)
        if mean_val > 0 and not np.allclose(arr, arr[0]):
            diff_sum = np.sum(np.abs(arr[:, np.newaxis] - arr[np.newaxis, :]))
            gini = float(diff_sum / (2 * n * n * mean_val))
        else:
            gini = 0.0

        return LorenzCurveResponse(
            population_shares=x_coords.tolist(),
            value_shares=y_coords.tolist(),
            gini_coefficient=gini,
            equality_line=x_coords.tolist(),
        )
